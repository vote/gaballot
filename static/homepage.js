(function () {
  var rows = [["Days Before", "General", "Runoff"]];
  var daysBeforeSeries = Object.keys(window.HOMEPAGE_GRAPH_DATA);

  daysBeforeSeries.forEach(function (daysBefore) {
    rows.push([
      // use negative value -- c3 automatically sorts ascending
      -daysBefore,
      window.HOMEPAGE_GRAPH_DATA[daysBefore].total_general,
      window.HOMEPAGE_GRAPH_DATA[daysBefore].total_special,
    ]);
  });

  c3.generate({
    bindto: "#homepage-graph",
    data: {
      x: "Days Before",
      rows: rows,
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
      },
    },
    grid: {
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
})();
