
import pymupdf


def extract_text_from_pdf(pdf_file):
    """
    Extract readable text from an uploaded PDF.

    Args:
        pdf_file: Streamlit uploaded PDF file.

    Returns:
        Extracted text from all PDF pages.
    """

    if pdf_file is None:
        raise ValueError("Please upload a PDF file.")

    pdf_bytes = pdf_file.read()

    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    try:
        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        ) as pdf:

            extracted_pages = []

            for page_number, page in enumerate(pdf, start=1):

                page_text = page.get_text("text").strip()

                if page_text:
                    extracted_pages.append(
                        f"[Page {page_number}]\n{page_text}"
                    )

        if not extracted_pages:
            raise ValueError(
                "No readable text found. This may be a scanned PDF."
            )

        return "\n\n".join(extracted_pages)

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Could not process this PDF: {error}"
        )
