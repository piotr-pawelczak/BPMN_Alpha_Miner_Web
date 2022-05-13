import os

from django.shortcuts import render, redirect
from .models import LogFile
from .forms import LogForm
import pandas as pd
import pm4py

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
            new_log_file = LogFile(log_file=request.FILES["log_file"])
            new_log_file.save()
            log_file_id = new_log_file.id

            log_file = LogFile.objects.get(id=log_file_id)
            logs_df = LogLoader(log_file.log_file.path).log_df
            columns = list(logs_df.columns)

            context = {"log_upload_form": form, "log_file": log_file, "columns": columns, "select_columns": True}
            return render(request, "bpmn/file_load.html", context)

    if request.method == 'POST' and 'load_columns' in request.POST:

        log_file_id = request.POST.get('log_file_id')

        case_id_column_name = request.POST["case_id"]
        activity_column_name = request.POST["activity"]
        start_timestamp_column_name = request.POST["start_timestamp"]

        log_file = LogFile.objects.get(id=log_file_id)
        log_file.case_id_column_name = case_id_column_name
        log_file.activity_column_name = activity_column_name
        log_file.timestamp_column_name = start_timestamp_column_name
        log_file.save()

        # logs = LogLoader(log_file.log_file.path, case_id_column_name, activity_column_name, start_timestamp_column_name)
        # logs.pick_columns()

        return redirect("bpmn:diagram", log_file_id)

    context = {"log_upload_form": form}
    return render(request, "bpmn/file_load.html", context)


def diagram_view(request, pk):

    log_file = LogFile.objects.get(id=pk)
    logs = LogLoader(log_file.log_file.path,
                     activity_column_name=log_file.activity_column_name,
                     case_id_column_name=log_file.case_id_column_name,
                     timestamp_column_name=log_file.timestamp_column_name)

    logs.pick_columns()
    logs_df = logs.log_df
    variants = logs.get_variants()

    NODE_THRESHOLD = 0
    EDGE_THRESHOLD = 0

    nodes_to_delete, edges_to_delete = Filter(logs_df).filter_graph(NODE_THRESHOLD, EDGE_THRESHOLD)

    G = MyGraph()
    miner = AlphaPlus(variants)
    miner.apply_filter(nodes_to_delete, edges_to_delete)
    miner.draw(G)

    cwd = os.getcwd()
    try:
        os.chdir('C:\\Users\\piotr\\Desktop\\ISZ\\Semestr 1\\MiAPB\\bpmn_web\\bpmn\\static\\svg')
        G.draw('simple_process_model.svg', prog='dot')
    finally:
        os.chdir(cwd)

    context = {"log_file_id": pk}
    return render(request, "bpmn/diagram.html", context)

