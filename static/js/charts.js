$(document).ready(function () {
  get_data();
  update_select();
});

// Define outside to function to destory
var myChart;

function get_data() {

  // Instantiate Variables
  var _data_values;
  var _data_labels;
  var _subreddit_name;

  var selected_text = $("#select-dropdown  :selected").text();

  if (selected_text == null) {
    selected_text = 'all'
  }

  // Create call for data at the /get_data endpoint
  $.ajax({
    url: "/get_data",
    type: "get",
    data: { vals: selected_text },

    success: function (response) {
      console.log('Successfully retrieved CHART data.')
      full_data = JSON.parse(response.payload);
      _data_values = full_data['data_values'];
      _data_labels = full_data['data_labels'];
      _subreddit_name = full_data['subreddit_name'];
    },

    complete: function () {
      console.log('Calling chart')
      print_chart(_data_values, _data_labels, _subreddit_name);
      update_rows(selected_text);
      update_hist_values(selected_text);
      update_card_values(selected_text);
    }
  });
}


function print_chart(_data_values, _data_labels, _subreddit_name) {
  
  if (myChart) {
    myChart.destroy();
  }
  
  // Set chart
  var ctx = document.getElementById("sentiment_histogram").getContext('2d');
  myChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: _data_labels,
      datasets: [{
        label: 'Subreddit: ' + _subreddit_name,
        data: _data_values,
        fillColor: 'rgb(0, 123, 255)',
      }]
    },
    options: {
      scales: {
        xAxes: [{
          display: true,
          barPercentage: 1.1,
          ticks: {
            max: 21,
          },
          gridLines: {
            color: "rgba(0, 0, 0, 0)",
          },
            scaleLabel: {
            display: true,
            labelString: "<<< More Negative Posts     More Positive Posts >>>",
          }
        }
        ],
        yAxes: [{
          ticks: {
            beginAtZero: true
          },
          gridLines: {
            color: "rgba(0, 0, 0, 0)",
          }
        }]
      }
    }
  });
}


function update_rows(subreddit_name) {
  
  var _data_labels;

  $.ajax({
    url: '/update_rows',
    type: 'get',
    data: { vals: subreddit_name },

    success: function (response) {
      console.log('Successfully retrieved ROW data.')

      $("#subreddit-table").empty();
      full_data = JSON.parse(response.payload);
      _data_labels = full_data['data_labels'];

      for (var j = 0; j < _data_labels.length; j++) {
        $("#subreddit-table").append(
          '<tr><td>' + _data_labels[j][0] +
          '</td><td>' + _data_labels[j][1] +
          '</td><td>' + _data_labels[j][2] +
          '</td><td>' + _data_labels[j][3] +
          '</td><td>' + _data_labels[j][4] +
          '</td><td>' + _data_labels[j][5] +
          '</td></tr>');
      }
    }
  });

}

function update_select() {

  var _data_labels;

  $.ajax({
    url: '/update_select',
    type: 'get',
    data: { vals: '' },

    success: function (response) {
      console.log('Successfully retrieved SELECT data.')

      $("#select-dropdown").empty();
      full_data = JSON.parse(response.payload);
      _data_labels = full_data['data_labels'];

      for (var i = 0; i <= _data_labels.length; i++) {
        $("#select-dropdown").append(
          $("<option></option>")
            .attr("value", _data_labels[i])
            .text(_data_labels[i])
        );
      }
    }
  });

}

function get_select_value() {

  var selected_text = $("#select-dropdown  :selected").text();
  console.log(selected_text);

  $.ajax({
    url: '/get_select_value',
    type: 'post',
    contentType: 'application/json',

    data: JSON.stringify(selected_text, null, '\t'),

    success: function (result) {
      console.log(result);
    }
  })
};

function update_card_values(selected_text) {

  // Cards
  var post_count = $("#post-count");
  var analyzed_count = $("#analyzed-count");
  var average_posts = $("#average-posts");
  var subreddit_count = $("#subreddit-count");
  var _data_values;
  
  $.ajax({
    url: '/update_card_values',
    type: 'get',
    data: { vals: selected_text },

    success: function (response) {
      console.log('Successfully retrieved CARD data.')
      full_data = JSON.parse(response.payload);
      _data_values = full_data['data_values'];

      // Set card values
      post_count.text(_data_values[0][0])
      analyzed_count.text(_data_values[1][0])
      average_posts.text(_data_values[2][0])
      subreddit_count.text(_data_values[3][0])
    }
  })
};

function update_hist_values(selected_text) {

  // Cards
  var positive_count = $("#positive-count");
  var negative_count = $("#negative-count");
  var neutral_count = $("#neutral-count");
  
  var _data_values;
  
  $.ajax({
    url: '/update_hist_values',
    type: 'get',
    data: { vals: selected_text },

    success: function (response) {
      console.log('Successfully retrieved HIST data.')
      full_data = JSON.parse(response.payload);
      _data_values = full_data['histogram_counts'];

      // Set histogram values
      positive_count.text(_data_values[0][1])
      negative_count.text(_data_values[0][0])
      neutral_count.text(_data_values[0][2])
    }
  })
};

