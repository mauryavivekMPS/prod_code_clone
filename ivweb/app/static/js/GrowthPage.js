var GrowthPage = (function() {
    var chartData;

    var addGrowth2 = function() {
        var data = growthData2();
        chartData.datum(data);
        nv.utils.windowResize(chart.update);
    };

    var showGraph = function(data) {
        var chart;
        var data;

        $('#chart').empty();

        nv.addGraph(function() {
            chart = nv.models.lineChart().options({
                height: 240,
                margin: {top: 30, right: 10, bottom: 40, left: 0},
                showYAxis: false,
                showLegend: false,
                transitionDuration: 300,
                useInteractiveGuideline: false
            });

            chart.xAxis.options({
                tickPadding: 15,
                tickValues: [
                    new Date(2014, 9, 1),
                    new Date(2015, 0, 1),
                    new Date(2015, 3, 1),
                    new Date(2015, 6, 1),
                    new Date(2015, 9, 1)
                ],
                tickFormat: function(d) {
                    return (d3.time.format('%b %Y'))(new Date(d));
                },
                showMaxMin: false
            });

            chartData = d3.select('#chart')
                .append('svg')
                .datum(data);

            chartData.call(chart);

            nv.utils.windowResize(chart.update);

            return chart;
        });
    };

    var showJournalsGraph = function() {
        $('.stats-ribbon .selectable').removeClass('active');
        $('#summary-graph-journals').addClass('active');
        $('.chart-title').html('Journals <span class="subtitle">Journals added over time</span>');
        showGraph(growthData1());
    };

    var showArticlesGraph = function() {
        $('.stats-ribbon .selectable').removeClass('active');
        $('#summary-graph-articles').addClass('active');
        $('.chart-title').html('Articles <span class="subtitle">Articles found over time</span>');
        showGraph(growthData2());
    };

    var showCitationsGraph = function() {
        $('.stats-ribbon .selectable').removeClass('active');
        $('#summary-graph-citations').addClass('active');
        $('.chart-title').html('Citations <span class="subtitle">Citations found over time</span>');
        showGraph(growthData3());
    };

    var init = function() {
        $('#summary-graph-journals').click(showJournalsGraph).click();
        $('#summary-graph-articles').click(showArticlesGraph);
        $('#summary-graph-citations').click(showCitationsGraph);
    };

    var growthData1 = function() {
        return [
            {
                area: true,
                values: [
                    {x: new Date(2014, 7, 1), y: 2},
                    {x: new Date(2014, 8, 1), y: 2},
                    {x: new Date(2014, 9, 1), y: 2},
                    {x: new Date(2014, 10, 1), y: 2},
                    {x: new Date(2014, 11, 1), y: 4},
                    {x: new Date(2015, 0, 1), y: 7},
                    {x: new Date(2015, 1, 1), y: 7},
                    {x: new Date(2015, 2, 1), y: 12},
                    {x: new Date(2015, 3, 1), y: 13},
                    {x: new Date(2015, 4, 1), y: 13},
                    {x: new Date(2015, 5, 1), y: 23},
                    {x: new Date(2015, 6, 1), y: 29},
                    {x: new Date(2015, 7, 1), y: 43},
                    {x: new Date(2015, 8, 1), y: 53},
                    {x: new Date(2015, 9, 1), y: 55},
                    {x: new Date(2015, 10, 1), y: 74},
                    {x: new Date(2015, 11, 1), y: 85}
                ],
                key: "Journals",
                color: "#0084ae",
                strokeWidth: 1,
                fillOpacity: .1
            }
        ];
    };

    var growthData2 = function() {
        return [
            {
                area: true,
                values: [
                    {x: new Date(2014, 7, 1), y: 2000},
                    {x: new Date(2014, 8, 1), y: 2100},
                    {x: new Date(2014, 9, 1), y: 2231},
                    {x: new Date(2014, 10, 1), y: 2632},
                    {x: new Date(2014, 11, 1), y: 4744},
                    {x: new Date(2015, 0, 1), y: 4997},
                    {x: new Date(2015, 1, 1), y: 5073},
                    {x: new Date(2015, 2, 1), y: 5200},
                    {x: new Date(2015, 3, 1), y: 5900},
                    {x: new Date(2015, 4, 1), y: 5953},
                    {x: new Date(2015, 5, 1), y: 15989},
                    {x: new Date(2015, 6, 1), y: 16922},
                    {x: new Date(2015, 7, 1), y: 33788},
                    {x: new Date(2015, 8, 1), y: 53665},
                    {x: new Date(2015, 9, 1), y: 55553},
                    {x: new Date(2015, 10, 1), y: 102333},
                    {x: new Date(2015, 11, 1), y: 134111}
                ],
                key: "Articles",
                color: "#009B81",
                strokeWidth: 1,
                fillOpacity: .1
            }
        ];
    };

    var growthData3 = function() {
        return [
            {
                area: true,
                values: [
                    {x: new Date(2014, 7, 1), y:   542000},
                    {x: new Date(2014, 8, 1), y:   552100},
                    {x: new Date(2014, 9, 1), y:   852231},
                    {x: new Date(2014, 10, 1), y:  902632},
                    {x: new Date(2014, 11, 1), y: 1114744},
                    {x: new Date(2015, 0, 1), y:  1284997},
                    {x: new Date(2015, 1, 1), y:  1335073},
                    {x: new Date(2015, 2, 1), y:  1799200},
                    {x: new Date(2015, 3, 1), y:  1805900},
                    {x: new Date(2015, 4, 1), y:  1905953},
                    {x: new Date(2015, 5, 1), y:  1915989},
                    {x: new Date(2015, 6, 1), y:  1916922},
                    {x: new Date(2015, 7, 1), y:  1953788},
                    {x: new Date(2015, 8, 1), y:  2013665},
                    {x: new Date(2015, 9, 1), y:  2025553},
                    {x: new Date(2015, 10, 1), y: 2002333},
                    {x: new Date(2015, 11, 1), y: 2124111}
                ],
                key: "Citations",
                color: "#FF6E00",
                strokeWidth: 1,
                fillOpacity: .1
            }
        ];
    };

    return {
        showJournalsGraph: showJournalsGraph,
        showArticlesGraph: showArticlesGraph,
        showCitationsGraph: showCitationsGraph,
        addGrowth2: addGrowth2,
        init: init
    };

})();
