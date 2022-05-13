$(document).ready(function () {
            $('.filter-slider').change(function () {
                let nodeThreshold = $('#node-slider').val();
                let edgeThreshold = $('#edge-slider').val();

                $("#node_threshold").val(nodeThreshold);
                $("#edge_threshold").val(edgeThreshold);

                $("#filter-form").submit();
            });
        });