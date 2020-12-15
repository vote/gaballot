// document.getElementById("homepage-graph").innerText = JSON.stringify(
//   window.HOMEPAGE_GRAPH_DATA
// );

var rows = [["Days Before", "General", "Runoff"]];

const daysBeforeSeries = Object.keys(window.HOMEPAGE_GRAPH_DATA);
daysBeforeSeries.sort().reverse();

daysBeforeSeries.forEach(function (daysBefore) {
  rows.push([
    // use negative value -- c3 automatically sorts ascending
    -daysBefore,
    window.HOMEPAGE_GRAPH_DATA[daysBefore].total_general,
    window.HOMEPAGE_GRAPH_DATA[daysBefore].total_special,
  ]);
});

console.log(rows);

var chart = c3.generate({
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
      lines: [{ value: 4015475, text: "Early Votes Cast In General" }],
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
