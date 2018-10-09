import os
import time
import markdown
import shutil
import datetime
import json

from utils import journal
from utils.upload import PATH_META_SELF

def generate_dashboard_content(app):
    index = '''<h1 class="display-3">Dashboard</h1>

    <hr />

<div class="container-fluid">
<div class="row">

  <div class="col-6">

<div class="card border-light" style="max-width: 30rem;">
  <div class="card-header">
<h3 class="card-title">Latest Release</h3>
  </div>
  <div class="card-body">

  <ul class="list-group list-group-flush">
    <li class="list-group-item">Cras justo odio</li>
    <li class="list-group-item">Dapibus ac facilisis in</li>
    <li class="list-group-item">Vestibulum at eros</li>
  </ul>

    </canvas><canvas id="myChart"></canvas>
  <script>
var ctx = document.getElementById("myChart").getContext('2d');
var myChart = new Chart(ctx, {
  type: 'pie',
  data: {
        labels: ["Failed", "Passed", "Error"],
        datasets: [{
          backgroundColor: [
            "rgba(183, 28, 28, .9)",
            "rgba(27, 94, 32, .9)",
            "rgba(1, 87, 155, .9)"
          ],
      data: [12, 19, 3]
    }]
  }
});
  </script>
  <a href="#" class="btn btn-light btn-block">Go to page</a>
  </div>
</div>
  </div>


  <div class="col-6">



<div class="card border-light" style="max-width: 60rem;">
  <div class="card-header">
<h3 class="card-title">Test Status Over Time</h3>
  </div>
  <div class="card-body">

    </canvas><canvas id="lineChart"></canvas>
  <script>
var ctx = document.getElementById("lineChart").getContext('2d');
var myChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
    datasets: [{
      label: 'errors',
      data: [2, 4, 1, 4, 2, 3, 4],
      backgroundColor: "rgba(1, 87, 155, .9)",
      steppedLine: 'before'
    }, {
      label: 'passed',
      data: [2, 29, 5, 5, 2, 3, 10],
      backgroundColor: "rgba(27, 94, 32, .9)",
      steppedLine: 'before'
    }, {
      label: 'failed',
      data: [12, 19, 3, 17, 6, 3, 7],
      backgroundColor: "rgba(183, 28, 28, .9)",
      steppedLine: 'before'
    }]
  }
});

  </script>
  <a href="#" class="btn btn-light btn-block">Go to page</a>
  </div>
</div>
  </div>


  </div>


</div>
</div>
'''
    return index

def generate_dashboard(app):
    new_index  = app['BLOB-HEADER']
    new_index += generate_dashboard_content(app)
    new_index += app['BLOB-FOOTER']
    path = os.path.join(app['PATH-GENERATE-DASHBOARD'], 'index.html')
    with open(path, 'w') as fd:
        fd.write(new_index)

async def generator(app):
    while True:
        value = await app['QUEUE-GENERATOR-DASHBOARD'].get()
        start = time.time()
        generate_dashboard(app)
        if app['DEBUG']:
            diff = time.time() - start
            msg = 'dashboard page generation completed in {:.4f} seconds'.format(diff)
            journal.log(app, msg)

