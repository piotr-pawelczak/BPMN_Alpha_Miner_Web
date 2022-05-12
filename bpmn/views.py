import os

from django.shortcuts import render
from alpha_miner.alpha_plus import AlphaPlus
from alpha_miner.graph import MyGraph
from alpha_miner.log_loader import LogLoader
from alpha_miner.filter import Filter
from .models import FilesUpload

from django.conf import settings


# Create your views here.

def home_view(request):

    context = {}
    return render(request, "bpmn/home_page.html", context)


def load_file_view(request):

    context = {}
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
