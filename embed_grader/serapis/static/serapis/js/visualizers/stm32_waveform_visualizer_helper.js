function draw_stm32_waveform_series(series_data) {

  timestamps = series_data.timestamps;
  values = series_data.values;
  label = series_data.label;
  div_id = series_data.id;

  waveform_data = [];
  for (var i = 0; i < series_data.timestamps.length; i++) {
    waveform_data.push({
      "ms": timestamps[i],
      "value": values[i],
    });
  }
  max_tick = timestamps[timestamps.length - 1];

  gid = "g_" + div_id;

  //charts[cid] = AmCharts.makeChart(div_id, {
  AmCharts.makeChart(div_id, {
    "type": "xy",
    "titles": [{"text": label}],
    "theme": "light",
    "autoMarginOffset": 25,
    "dataProvider": waveform_data,
    "graphs": [{
      "id": gid,
      "balloonText": "ms: [[ms]]<br/><b>value: [[value]]</b>",
      "type": "step",
      "lineThickness": 2,
      "bullet": "square",
      "bulletAlpha": 0,
      "bulletSize": 4,
      "bulletBorderAlpha": 0,
      //"valueField": "value"
      "xField": "ms",
      "yField": "value",
    }],
    "valueAxes": [
      {
        "axisAlpha":0,
      },
      {
        "axisAlpha": 0,
        "title": "Time in millisecond",
        "position": "bottom",
        "maximum": max_tick,
      }
    ],
    "chartScrollbar": {},
    "chartCursor": {},
    "export": {
      "enabled": true
    }
  });

  //function zoomChart() {
  //  charts[cid].zoomToIndexes(0, 20);
  //}
  //charts[cid].addListener("dataUpdated", zoomChart);
}
