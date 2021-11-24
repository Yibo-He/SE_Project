import os
from ast import literal_eval
from app.tools.formatter import formatter
import docx
import PyPDF2
from flask import (
    Blueprint, flash, g, json, redirect, render_template, request, session, url_for, jsonify
)
from werkzeug.exceptions import abort

from .auth import login_required
from ..db import get_db, allocate_docID
from ..tools.formatter import formatter
from ..tools.pdf import pdf2chart, save_tables, process
from flask import send_from_directory, current_app, make_response

bp = Blueprint('doc_formatter', __name__)


@bp.route('/')
def index():
    if g.user is None:
        return {}
    else:
        return g.user


@bp.route('/upload_doc', methods=['POST'])
@login_required
def upload_doc():
    files_dict = request.files
    print(files_dict)
    # for i, j in files_dict.items():
    #     print(i, j)
    
    file_template = {'state': 0, 'info':'success', 'filename':"invalid"}  # to mark the state
    jsondata = []
    error = None
    if files_dict is None:
        error = 'No files uploaded'
        file_info = file_template.copy()
        file_info['state'] = 1
        file_info['info'] = error
        jsondata.append(file_info)
        return jsonify(jsondata)

    if error is None:
        for file_obj in files_dict.values():
            print(file_obj)
            file_info = file_template.copy()
            status, info = allocate_docID(session.get('user_id'), file_obj.filename)
            if status == True:
                try:
                    docID = info["idx"]
                    file_name = str(session.get('user_id')) + '&' +  str(docID) + '&' + file_obj.filename
                    file_path = os.path.join('./temp/', file_name)
                    file_obj.save(file_path)
                    file_info["filename"] = file_name
                except:
                    error = 'Uploading Error' 
                    file_info['state'] = 2
                    file_info['info'] = error
            else:
                error = 'Database Error'
                file_info['state'] = 2
                file_info['info'] = error
            print(file_info)
            jsondata.append(file_info)
    print(jsondata)
    # all the succussfully uploaded files are labeled with state 0
    return jsonify(jsondata)


@bp.route('/run_formatter', methods=['POST'])
@login_required
def run_formatter():
    # file_names = literal_eval(request.form['file_names'])
    file_names = request.form['file_names'].split(',')
    print(file_names)
    # print(type(file_names))
    # print(file_names)
    requirements = get_reqs(request.form)
    print(requirements)
    formatted_names = []
    jsondata = []
    file_template = {'state': 0, 'info':'success', 'formatted_name':"invalid", 'original_name': "invalid"}
    # jsondata = {'state': 0, 'info':'success', 'formatted_names':[] }  # to mark the state
    error = check_file_permission(file_names)
    if error is not None:
        file_info = file_template.copy()
        file_info['state'] = 1
        file_info['info'] = error
        jsondata.append(file_info)
        return jsonify(jsondata)
    else:
        for file_name in file_names:
            file_info = file_template.copy()
            file_info['original_name'] = file_name
            try:
                raw_doc = docx.Document(os.path.join('./temp/', file_name))
            except:
                error = 'No such file: ' + file_name
                file_info['state'] = 3
                file_info['info'] = "File not found"
                jsondata.append(file_info)
                continue
            try:
                formatted_doc = formatter(raw_doc, requirements)
                formatted_name = 'formatted_' + file_name
                formatted_doc.save(os.path.join('./temp/', formatted_name))
                file_info['formatted_name'] = formatted_name
            except:
                error = 'failed to transform the file: ' + file_name
                file_info['state'] = 2
                file_info['info'] = error
            jsondata.append(file_info)
          # only successful files
    # flash(error)
    # return jsonify(formatted_names)
    print(jsondata)
    return jsonify(jsondata)

@bp.route('/run_pdf2chart', methods=['POST'])
@login_required
def run_pdf2chart():
    # file_names = literal_eval(request.form['file_names'])
    file_names = request.form['file_names'].split(',')
    print(file_names)
    # print(type(file_names))
    # print(file_names)
    # pages = [int(x) for x in request.form['pages'].split(' ') if x!='']
    # print(pages)
    pages = request.form['src_pages']
    chart_names = []
    jsondata = []
    file_template = {'state': 0, 'info':'success', 'chart_name':"invalid", 'original_name': "invalid"}
    # jsondata = {'state': 0, 'info':'success', 'formatted_names':[] }  # to mark the state
    error = check_file_permission(file_names)
    if error is not None:
        file_info = file_template.copy()
        file_info['state'] = 1
        file_info['info'] = error
        jsondata.append(file_info)
        return jsonify(jsondata)
    else:
        for file_name in file_names:
            file_info = file_template.copy()
            file_info['original_name'] = file_name
            try:
                # raw_doc = docx.Document(os.path.join('./temp/', file_name))
                # print(os.getcwd())
                document_path = os.path.join('./temp/', file_name)
                # raw_doc = PyPDF2.PdfFileReader(open(r'D:\Downloads\EasyFile\temp\None&0&test.pdf','rb'))
                # print(os.path.exists(document_path))
                assert os.path.exists(document_path)
                '''
                with open(document_path,"rb") as f:
                    print('line 153', document_path)
                    raw_doc = PyPDF2.PdfFileReader(f)
                '''
                
            except:
                error = 'No such file: ' + file_name
                file_info['state'] = 3
                file_info['info'] = "File not found"
                jsondata.append(file_info)
                continue
            try:
            # formatted_doc = formatter(raw_doc, requirements)
            # print('line 167')
            # tables = pdf2chart(raw_doc, pages)
            # tables = process(document_path, )
            # print('line 169')
                formatted_name = 'chart_' + os.path.splitext(file_name)[0] + '.zip'
                save_path = os.path.join('./temp/', formatted_name)
                ret = process(document_path,format='excel',ext='xlsx',rules=[pages])
                with open(save_path,'wb') as f:
                    f.write(ret)
                # save_tables(tables, save_path)
                # print('line 173')
                file_info['formatted_name'] = formatted_name
            
            except:
                error = 'failed to transform the file: ' + file_name
                file_info['state'] = 2
                file_info['info'] = error
            
            jsondata.append(file_info)
          # only successful files
    # flash(error)
    # return jsonify(formatted_names)
    print(jsondata)
    return jsonify(jsondata)


@bp.route('/download/<filename>', methods=['GET','POST'])
@login_required
def download_doc(filename):

    # jsondata = {'state': 0, 'info':'success'}  # to mark the state
    error = check_formatted_file_permission(filename)
    if error is None:
        response = make_response(send_from_directory(current_app.config['TEMP_PATH'], filename, as_attachment=True))
        response.headers["Access-Control-Expose-Headers"] = "Content-disposition"
        return response
    return None

def check_formatted_file_permission(filename):

    if str(session.get('user_id')) != filename.split("&")[0].split('_')[-1]:
        return "Permission denied"
    return None


def check_file_permission(file_names):
    for fn in file_names:
        if str(session.get('user_id')) != fn.split("&")[0]:
            # print(str(session.get("user_id")), fn)
            return "Permission denied"
    #else:
    return None

def get_reqs(form):
    # return [
    #     {"src_str":"用户","src_typeface":"等线","src_size":16,"src_color":"000000",
    #     "dst_str":"我","dst_typeface":"宋体","dst_size":12,"dst_color":"66ccff"}]
    req_dict = {}
    for k,v in form.items():
        if k != 'file_names':
            req_dict[k] = v if k != 'src_size' and k!= 'dst_size' else float(v)
    return [req_dict]
    '''
    # just for test
    return [
        {"src_str":"用户","src_typeface":"等线","src_size":16,"src_color":"000000",
        "dst_str":"我","dst_typeface":"宋体","dst_size":12,"dst_color":"66ccff"},

        {"src_str":"图","src_typeface":"","src_size":0,"src_color":"",
        "dst_str":"我","dst_typeface":"宋体","dst_size":12,"dst_color":"66ccff"},
        
        {"src_str":'”',"src_typeface":"","src_size":16,"src_color":"",
        "dst_str":'”',"dst_typeface":"宋体","dst_size":16,"dst_color":"000000"}]
    '''
    # return [{}, {}]

def del_temp_files(file_paths):
    pass

def sweep_temp_files(user_id):
    pass