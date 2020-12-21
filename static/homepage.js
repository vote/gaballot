
(function () {
  var daysBeforeSeries = Object.keys(window.HOMEPAGE_GRAPH_DATA['combined']);
  var daysBeforeCol = ['Days Before'];
  var combinedGeneral = ['combinedGeneral'];
  var combinedRunoff = ['combinedRunoff'];
  var demGeneral = ['demGeneral'];
  var demRunoff = ['demRunoff'];
  var repGeneral = ['repGeneral'];
  var repRunoff = ['repRunoff'];

  daysBeforeSeries.forEach(function (daysBefore) {
    // use negative value -- c3 automatically sorts ascending
    daysBeforeCol.push(-daysBefore);
    combinedGeneral.push(window.HOMEPAGE_GRAPH_DATA['combined'][daysBefore].total_general);
    combinedRunoff.push(window.HOMEPAGE_GRAPH_DATA['combined'][daysBefore].total_special);
    demGeneral.push(window.HOMEPAGE_GRAPH_DATA['D'][daysBefore].total_general);
    demRunoff.push(window.HOMEPAGE_GRAPH_DATA['D'][daysBefore].total_special);
    repGeneral.push(window.HOMEPAGE_GRAPH_DATA['R'][daysBefore].total_general);
    repRunoff.push(window.HOMEPAGE_GRAPH_DATA['R'][daysBefore].total_special);
  });

  var graph = c3.generate({
    bindto: "#homepage-graph",
    data: {
      x: "Days Before",
      columns: [
        daysBeforeCol, combinedGeneral, combinedRunoff
      ],
      colors: {
        combinedGeneral: '#6f42c1a0',
        combinedRunoff: '#6f42c1',
        demGeneral: '#007bffa0',
        demRunoff: '#007bff',
        repGeneral: '#dc3545a0',
        repRunoff: '#dc3545'
      },
      regions: {
        combinedGeneral: [ {style: 'dashed'} ],
        demGeneral: [ {style: 'dashed'} ],
        repGeneral: [ {style: 'dashed'} ]
      },
      names: {
        combinedGeneral: "General 2020",
        combinedRunoff: "Runoff 2021",
        demGeneral: "Democrats General 2020",
        demRunoff: "Democrats Runoff 2021",
        repGeneral: "Republicans General 2020",
        repRunoff: "Republicans Runoff 2021"
      }
    },
    axis: {
      x: {
        label: "Days Before Election",
        tick: {
          format: function (x) {
            return -x;
          },
        },
      },
      y: {
        label: "Votes Cast",
        min: 0,
        max: 4000000,
        padding: {
          top: 20,
          bottom: 0
        }
      },
    },
    grid: {
      x: {
        lines: [
          { value: -23, text: "In person early voting starts" },
        ],
      },
      y: {
        lines: [
          { value: 4015475, text: "4,015,475 Early Votes Cast In General" },
        ],
      },
    },
    tooltip: {
      format: {
        title: function (d) {
          return -d + " days before";
        },
      },
    },
  });

  document.getElementById('partisan-toggle').addEventListener('click', function(e) {
    if (e.toElement.checked) {
      graph.load({
        columns: [
          daysBeforeCol,
          demGeneral,
          demRunoff,
          repGeneral,
          repRunoff
        ],
        unload: [
          'combinedGeneral',
          'combinedRunoff'
        ]
      });
      graph.axis.max(undefined);
    } else {
      graph.load({
        columns: [
          daysBeforeCol,
          combinedGeneral,
          combinedRunoff
        ],
        unload: [
          'demGeneral',
          'demRunoff',
          'repGeneral',
          'repRunoff'
        ]
      });
      graph.axis.max(4000000);
    }
  });
})();
