<template>
  <div id="app">
    <form class="model-upload-form" method="POST">
      <legend>Load Another Model</legend>
      <input ref="upload" type="file" name="file-upload" multiple="" accept="application/JSON" @change="onFileChange">
      <button class="btn btn-primary" @click="renderModel">Load Model</button>
    </form>
  </div>
</template>

<script>
import json_data from '../src/assets/test_models/test_data.json'

export default {
  name: 'app',
  data () {
    return {
      msg: 'This is a sample SBML Report',
      data: json_data,
    }
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

#sample-list {
  display: block;
  font-size: large;
}

.model-upload-form{
  border: 2px black;
  padding: 20px;
}

h1, h2 {
  font-weight: normal;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}

@import'~bootstrap/dist/css/bootstrap.css';
</style>
