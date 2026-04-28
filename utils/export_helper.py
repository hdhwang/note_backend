import io
import zipfile
from datetime import datetime
from openpyxl import Workbook
from django.http import HttpResponse

def export_to_zip(data, field_mappings, menu_name):
    """
    data: 필터링된 데이터 (쿼리셋 또는 리스트)
    field_mappings: { 'field': 'Excel Label' }
    menu_name: 메뉴명 (파일명 생성 시 사용)
    """
    # 1. 엑셀 파일 생성
    wb = Workbook()
    ws = wb.active
    ws.title = menu_name

    # 헤더 작성
    headers = list(field_mappings.values())
    ws.append(headers)

    # 데이터 작성
    fields = list(field_mappings.keys())
    for item in data:
        row = []
        for field in fields:
            if isinstance(item, dict):
                value = item.get(field, "")
            else:
                value = getattr(item, field, "")
            
            # datetime 객체인 경우 문자열로 변환
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            row.append(value)
        ws.append(row)

    # 엑셀을 메모리에 저장
    excel_io = io.BytesIO()
    wb.save(excel_io)
    excel_data = excel_io.getvalue()

    # 2. ZIP 파일 생성 (엑셀 파일명과 ZIP 파일명을 동일한 베이스명으로 설정)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{menu_name}_{timestamp}"
    excel_filename = f"{filename}.xlsx"
    zip_filename = f"{filename}.zip"

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(excel_filename, excel_data)
    
    zip_data = zip_io.getvalue()

    # 3. 응답 반환
    from django.utils.encoding import escape_uri_path
    response = HttpResponse(zip_data, content_type='application/zip')
    # 브라우저에서 한글 파일명이 깨지지 않도록 escape_uri_path 사용
    response['Content-Disposition'] = f"attachment; filename={escape_uri_path(zip_filename)}"
    
    return response
