import os

from django.shortcuts import render, redirect
from .models import LogFile
from .forms import LogForm
import pandas as pd

from alpha_miner.alpha_plus import AlphaPlus
from alpha_miner.graph import MyGraph
from alpha_miner.log_loader import LogLoader
from alpha_miner.filter import Filter

# Create your views here.


def home_view(request):

    context = {}
    return render(request, "bpmn/home_page.html", context)


def load_file_view(request):

    form = LogForm()

    if request.method == 'POST' and 'load_file' in request.POST:
        form = LogForm(request.POST, request.FILES)
        if form.is_valid():
            LogFile.objects.all().delete()
            new_log_file = LogFile(log_file=request.FILES["log_file"])
            new_log_file.save()
            log_file = LogFile.objects.get(id=new_log_file.id)

            logs_df = pd.read_csv(log_file.log_file.path)
            columns = list(logs_df.columns)

            # logs = LogLoader(log_file.log_file.path)
            # logs_df = logs.read_logs()
            # columns = list(logs_df.columns)

            context = {"log_upload_form": form, "log_file": log_file, "columns": columns, "select_columns": True}
            return render(request, "bpmn/file_load.html", context)

    if request.method == 'POST' and 'load_columns' in request.POST:
        form = LogForm(request.POST, request.FILES)

        case_id_column_name = request.POST["case_id"]
        activity_column_name = request.POST["activity"]
        start_timestamp_column_name = request.POST["start_timestamp"]

        log_file = LogFile.objects.first()

        logs = LogLoader(log_file.log_file.path, case_id_column_name, activity_column_name, start_timestamp_column_name)
        logs_df = logs.read_logs()
        columns = list(logs_df.columns)
        variants = logs.get_variants()
        
        context = {"log_upload_form": form, "log_file": log_file, "columns": columns, "variants": variants}
        return render(request, "bpmn/file_load.html", context)

    context = {"log_upload_form": form}
    return render(request, "bpmn/file_load.html", context)


def diagram_view(request):

    context = {}
    return render(request, "bpmn/diagram.html", context)

# def home_view(request):
#
#     self_loops = None
#
#     if request.method == "POST":
#         file = request.FILES["file"]
#         logs = FilesUpload.objects.create(file=file)
#         logs.save()
#
#         LOG_PATH = os.path.join(settings.MEDIA_ROOT, str(file))
#
#         G = MyGraph()
#         logs = LogLoader(LOG_PATH)
#         variants = logs.get_variants()
#         logs_df = logs.read_logs()
#
#         NODE_THRESHOLD = 0
#         EDGE_THRESHOLD = 0
#         nodes_to_delete, edges_to_delete = Filter(logs_df).filter_graph(NODE_THRESHOLD, EDGE_THRESHOLD)
#
#         miner = AlphaPlus(variants)
#         miner.apply_filter(nodes_to_delete, edges_to_delete)
#         miner.draw(G)
#
#         self_loops = miner.self_loop_events
#
#         cwd = os.getcwd()
#         try:
#             os.chdir('C:\\Users\\piotr\\Desktop\\ISZ\\Semestr 1\\MiAPB\\bpmn_web\\bpmn\\static\\svg')
#             G.draw('simple_process_model.svg', prog='dot')
#         finally:
#             os.chdir(cwd)
#
#     context = {}
#     return render(request, 'bpmn/base.html', context=context)
