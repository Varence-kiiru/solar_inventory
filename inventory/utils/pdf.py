# inventory/utils/pdf.py
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

# inventory/views.py
from .utils.pdf import render_to_pdf

class InvoicePDFView(DetailView):
    model = Sale
    template_name = 'inventory/invoice_pdf.html'
    
    def get(self, request, *args, **kwargs):
        sale = self.get_object()
        pdf = render_to_pdf(self.template_name, {'sale': sale})
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Invoice_{sale.id}.pdf"
            content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Error generating PDF", status=400)