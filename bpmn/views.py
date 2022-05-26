import os

from django.shortcuts import render, redirect
from .models import LogFile
from .forms import LogForm
from django.contrib.staticfiles import finders

from alpha_miner.alpha_plus import AlphaPlus
from alpha_miner.graph import MyGraph
from alpha_miner.log_loader import LogLoader
from alpha_miner.filter import Filter
from alpha_miner.column_match import get_activity_columns, get_case_id_columns, get_date_columns

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
            
            case_id_suggestion = get_case_id_columns(logs_df)[0]
            activity_suggestion = get_activity_columns(logs_df)[0]
            timestamp_suggestion = get_date_columns(logs_df)[0]

            context = {"log_upload_form": form, "log_file": log_file, "columns": columns, "select_columns": True,
             "case_id_suggestion": case_id_suggestion, "activity_suggestion": activity_suggestion, "timestamp_suggestion": timestamp_suggestion}
            return render(request, "bpmn/file_load.html", context)

    if request.method == 'POST' and 'load_columns' in request.POST:

        log_file_id = request.POST.get('log_file_id')

        case_id_column_name = request.POST.get("case_id")
        activity_column_name = request.POST.get("activity")
        start_timestamp_column_name = request.POST.get("start_timestamp")

        log_file = LogFile.objects.get(id=log_file_id)
        log_file.case_id_column_name = case_id_column_name
        log_file.activity_column_name = activity_column_name
        log_file.timestamp_column_name = start_timestamp_column_name
        log_file.save()

        return redirect("bpmn:diagram", log_file_id)

    context = {"log_upload_form": form}
    return render(request, "bpmn/file_load.html", context)


def display_graph(logs_df, variants, node_threshold, edge_threshold):

    nodes_to_delete, edges_to_delete = Filter(logs_df).filter_graph(node_threshold, edge_threshold)

    G = MyGraph()
    miner = AlphaPlus(variants)
    miner.apply_filter(nodes_to_delete, edges_to_delete)
    miner.draw(G)

    print("========== DEBUG INFO =============")
    print(f"events: {miner.events}")
    print(f"Direct: {miner.direct_succession}")
    print(f"Causality: {miner.causality}")
    print(f"Xl: {miner.Yl}")
    print(f"Yl: {miner.Yl}")
    print(f"self: {miner.self_loop_events}")
    print(f"parallel: {miner.parallel_events}")
    print(miner.triangles)

    cwd = os.getcwd()
    svg_path = finders.find('svg/')
    try:
        os.chdir(svg_path)
        G.draw('simple_process_model.svg', prog='dot')
    finally:
        os.chdir(cwd)

    return nodes_to_delete, edges_to_delete


def diagram_view(request, pk):

    NODE_THRESHOLD = 0
    EDGE_THRESHOLD = 0

    log_file = LogFile.objects.get(id=pk)

    logs = LogLoader(log_file.log_file.path,
                     activity_column_name=log_file.activity_column_name,
                     case_id_column_name=log_file.case_id_column_name,
                     timestamp_column_name=log_file.timestamp_column_name)

    logs.pick_columns()

    logs_df = logs.log_df

    variants = logs.get_variants()
    traces = Filter(logs_df).traces

    traces_list = list(traces['trace'])
    traces_count = list(traces['count'])
    traces_length = [len(elem) for elem in traces_list]
    traces_info = zip(traces_list, traces_length, traces_count)

    events = logs.get_event_count()

    if 'node_threshold_input' in request.POST:
        NODE_THRESHOLD = int(request.POST.get('node_threshold_input'))
        EDGE_THRESHOLD = int(request.POST.get('edge_threshold_input'))

    nodes_to_delete, edges_to_delete = display_graph(logs_df, variants, NODE_THRESHOLD, EDGE_THRESHOLD)
    context = {"log_file_id": pk, "node_threshold": NODE_THRESHOLD, "edge_threshold": EDGE_THRESHOLD,
               "event_counter": events, "variants": variants, "traces_info": traces_info,
               "edges_to_delete": edges_to_delete, "nodes_to_delete": nodes_to_delete}

    return render(request, "bpmn/diagram.html", context)

