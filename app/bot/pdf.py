from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from typing import Callable
from app.data.models import Word
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from typing import List
import logging
from app.decorators import log_calls
from app.config import send_document_url
from httpx import AsyncClient


logger = logging.getLogger(__name__)

pdfmetrics.registerFont(TTFont('NotoSans', '/Users/oleg/Downloads/Noto_Sans,Noto_Sans_JP/Noto_Sans_JP/static/NotoSansJP-Regular.ttf'))

class PDF:
    def __init__(self,
                 client: AsyncClient,
                 send_msg_func: Callable,
                 style: str = 'Normal',
                 font_name: str = 'NotoSans',
                 font_size: int = 10,
                 ):
        self.style = style
        self.font_name = font_name
        self.font_size = font_size
        self.client = client
        self.send_msg_func = send_msg_func
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.normal = self.styles[self.style]
        self.normal.fontName = self.font_name
        self.normal.fontSize = self.font_size


    @log_calls
    async def generate_pdf(self, words: List[Word],) -> dict|bool:

        buffer = BytesIO()

        pdf = SimpleDocTemplate(buffer, pagesize=A4)

        self.elements.clear()
        logger.debug('elements: %s, %s',  self.elements, len(self.elements))

        if not words:
            return {
                'success': False,
                'buffer': None,
                'details': 'list of words is empty',
            }

        data = [[Paragraph("№", self.normal), Paragraph("Слово", self.normal), Paragraph("Перевод", self.normal)]]

        for i, word in enumerate(words, 1):
            data.append([Paragraph(str(i), self.normal),
                         Paragraph(word.word or "", self.normal),
                         Paragraph(word.translate or "", self.normal)])

        table = Table(data, colWidths=[30, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))

        self.elements.append(table)
        logger.debug('elements after adding: %s, %s', self.elements, len(self.elements))

        elements_for_bild = self.elements.copy()
        pdf.build(elements_for_bild)
        buffer.seek(0)

        return {
            'success': True,
            'buffer': buffer,
            'details': f'PDF generated: {len(words)} words'
        }


    async def send_pdf(self, chat_id: int, buffer: BytesIO):
        buffer.seek(0)

        if buffer.getbuffer().nbytes == 0:
            await self.send_msg_func(chat_id, 'There are no words in the list')

            return {
                'access': False,
                'details':'words_list is empty'
            }


        files = {
          'document': ('words.pdf', buffer, 'application/pdf')
        }
        data= {
            'chat_id': chat_id,
        }

        try:
            resp = await self.client.post(send_document_url, data=data, files=files)
            logger.info('response from Telegram: %s, %s', resp.status_code, resp.text())
            if resp.status_code != 200:
                logger.exception(f'Telegram API error: {resp.json()}')
                try:
                    error_json = await resp.json()
                except:
                    error_json = {}
                description = error_json.get('description', 'Unknown error')
                return {'success': False, 'details': f'Telegram error: {description}'}

            resp.raise_for_status()
            return {
                'success': True,
                'details': 'PDF has been sent successfully'
            }
        except Exception as e:
            logger.exception('sending pdf failed')
            return {
                'success': False,
                'details': f'Network error: {str(e)}'
            }