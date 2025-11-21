import pytest
from reportlab.platypus import Table
import httpx
import logging

from drafts.conftest import mock_httpx_client

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
class TestPDF:

    async def test_generate_pdf_empty_list(self, pdf_instance):

        result = await pdf_instance.generate_pdf([])

        assert result['success'] is False
        assert result['buffer'] is None
        assert 'empty' in result['details'].lower()
        assert len(pdf_instance.elements) == 0

    async def test_generate_pdf_with_words(self, pdf_instance, sample_words):

        result = await pdf_instance.generate_pdf(sample_words)
        logger.debug('result: %s', result)
        logger.debug(f"TEST LOG: len(elements) = {len(pdf_instance.elements)}")

        assert result['success'] is True
        buffer = result['buffer']
        assert buffer is not None

        buffer.seek(0)
        header = buffer.read(5)
        assert header == b"%PDF-"

        size = buffer.getbuffer().nbytes
        assert size > 500

        assert len(pdf_instance.elements) == 1
        assert isinstance(pdf_instance.elements[0], Table)

    async def test_generate_pdf_clears_previous_state(self, pdf_instance, sample_words):

        last_result = await pdf_instance.generate_pdf(sample_words)
        last_buffer = last_result['buffer']

        new_result = await pdf_instance.generate_pdf([sample_words[0]])
        new_buffer = new_result['buffer']

        assert new_buffer is not last_buffer
        assert len(pdf_instance.elements) == 1
        assert new_buffer.getbuffer().nbytes > 0

    async def test_send_pdf_success(self, pdf_instance, mock_httpx_client, sample_words):

        gen_result = await pdf_instance.generate_pdf(sample_words)
        assert gen_result['success']

        buffer = gen_result['buffer']

        result = await pdf_instance.send_pdf(chat_id=999, buffer=buffer)

        mock_httpx_client.post.assert_called_once()
        call_kwargs = mock_httpx_client.post.call_args.kwargs

        assert call_kwargs['data'] == {'chat_id': 999}
        files = call_kwargs['files']
        assert files['document'][0] == 'words.pdf'
        assert files['document'][2] == 'application/pdf'

        sent_buffer = files["document"][1]
        assert sent_buffer.tell() == 0

        assert result['success'] is True
        assert 'successfully' in result['details']

    async def test_send_pdf_network_error(self, pdf_instance, mock_httpx_client, sample_words):

        mock_httpx_client.post.side_effect = httpx.ConnectTimeout('Timeout')

        res = await pdf_instance.generate_pdf(sample_words)
        buffer = res['buffer']

        result = await pdf_instance.send_pdf(chat_id=123, buffer=buffer)

        assert result["success"] is False
        assert "Исключение" in result["details"] or "timeout" in result["details"].lower()