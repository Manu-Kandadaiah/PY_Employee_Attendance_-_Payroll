import uuid
import zipfile
from pathlib import Path
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from ...services.dataset_reporting import read_data, clean_data, write_report

analytics_bp = Blueprint('analytics', __name__)


def base_dir():
    return Path(current_app.instance_path) / 'analytics_outputs' / str(current_user.id)


@analytics_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if current_user.role not in ('admin', 'hr'):
        abort(403)
    if request.method == 'POST':
        uploaded = request.files.get('dataset')
        name = secure_filename(uploaded.filename or '') if uploaded else ''
        if not name or Path(name).suffix.lower() not in ('.csv', '.xlsx'):
            flash('Select a CSV or XLSX file.', 'danger')
            return redirect(url_for('analytics.index'))
        job = uuid.uuid4().hex
        folder = base_dir() / job
        folder.mkdir(parents=True, exist_ok=False)
        try:
            incoming = folder / ('input' + Path(name).suffix.lower())
            uploaded.save(incoming)
            if incoming.stat().st_size > 10 * 1024 * 1024:
                raise ValueError('Maximum file size is 10 MB')
            headers, rows, stats = clean_data(read_data(incoming))
            write_report(headers, rows, stats, folder)
            incoming.unlink()
            with zipfile.ZipFile(folder/'report_bundle.zip', 'w', zipfile.ZIP_DEFLATED) as z:
                for file in folder.iterdir():
                    if file.is_file() and file.name != 'report_bundle.zip':
                        z.write(file, file.name)
            flash('Data cleaned and chart report generated.', 'success')
        except Exception as exc:
            import shutil
            shutil.rmtree(folder, ignore_errors=True)
            flash(f'Import failed: {exc}', 'danger')
        return redirect(url_for('analytics.index'))
    folders = sorted((x for x in base_dir().glob('*') if x.is_dir()), reverse=True)[:30] if base_dir().exists() else []
    return render_template('analytics/index.html', folders=folders)


@analytics_bp.get('/download/<job>')
@login_required
def download(job):
    if current_user.role not in ('admin', 'hr'):
        abort(403)
    if len(job) != 32 or any(c not in '0123456789abcdef' for c in job):
        abort(404)
    file = base_dir() / job / 'report_bundle.zip'
    if not file.is_file():
        abort(404)
    return send_file(file, as_attachment=True, download_name=f'analytics_{job[:8]}.zip')
