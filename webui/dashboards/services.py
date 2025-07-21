import plotly.graph_objects as go
from typing import List

def create_plotly_html(figures: List[go.Figure]) -> str:
    """
    Формирует HTML с Plotly графиками из списка figure-объектов.
    :param figures: Список объектов plotly.graph_objects.Figure
    :return: HTML-код с графиками, которые можно перетаскивать и изменять размер
    """
    figures_json = [fig.to_json() for fig in figures]
    graphs_html = ""
    for i, fig_json in enumerate(figures_json):
        graphs_html += f'''
        <div id="graph{i}" class="draggable resizable" style="width:400px; height:300px; padding:10px; top: {i * 350}px; left: {50 * (i + 1)}px;"></div>
        '''
    html_code = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.min.js"></script>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
        <style>
            body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f0f0f0; overflow: auto; }}
            .draggable {{ position: absolute; border: 1px solid #ddd; background-color: #fff; box-shadow: 5px 5px 15px rgba(0,0,0,0.2); z-index: 100; cursor: move; }}
        </style>
    </head>
    <body>
        {graphs_html}
        <script>
            function checkAndExpandWorkspace(ui) {{
                const buffer = 100;
                const elementBottom = ui.position.top + ui.helper.height();
                const elementRight = ui.position.left + ui.helper.width();
                if (elementBottom + buffer > $(document).height()) {{
                    $("body").css("height", elementBottom + buffer + "px");
                }}
                if (elementRight + buffer > $(document).width()) {{
                    $("body").css("width", elementRight + buffer + "px");
                }}
            }}
            function renderPlotlyGraph(graphId, figureJson) {{
                const figure = JSON.parse(figureJson);
                Plotly.newPlot(graphId, figure.data, figure.layout);
            }}
            $(document).ready(function() {{
                {''.join([f'renderPlotlyGraph("graph{i}", `{fig_json}`);' for i, fig_json in enumerate(figures_json)])}
            }});
            $(function() {{
                $(".draggable").draggable({{
                    drag: function(event, ui) {{ checkAndExpandWorkspace(ui); }}
                }}).resizable({{
                    stop: function(event, ui) {{
                        const graphId = ui.helper[0].id;
                        const width = ui.size.width;
                        const height = ui.size.height;
                        Plotly.relayout(graphId, {{ width: width - 20, height: height - 20 }});
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    '''
    return html_code 