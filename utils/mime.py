MIME_TYPES = dict(png='image/png',
                  svg='image/svg+xml',
                  xlsx='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  sdf='chemical/x-mdl-sdfile', zip='application/zip',
                  csv='text/csv', mol='chemical/x-mdl-molfile', smi='chemical/x-daylight-smiles',
                  cif='chemical/x-cif', pdf='application/pdf')


def get_content_type(path):
    lwr = path.lower()
    if lwr.endswith('.mol'):
        return MIME_TYPES['mol']
    if lwr.endswith('.sdf'):
        return MIME_TYPES['sdf']
    if lwr.endswith('.smi'):
        return MIME_TYPES['smi']
    if lwr.endswith('.cif'):
        return MIME_TYPES['cif']
    if lwr.endswith('.pdf'):
        return MIME_TYPES['pdf']
    if lwr.endswith('.csv'):
        return MIME_TYPES['csv']
    if lwr.endswith('.xlsx'):
        return MIME_TYPES['xlsx']
