<template>
  <div id="app">
    <h1>{{ msg }}</h1>

    <br>
    <u><h2>Sample SBML Rendering </h2></u>

    <br>
    <strong>
      <h4>{{ data.model_sid }}: {{ data.model_name }}</h4>
    </strong>

    <ul>
      <li  id="sample-list" v-for="reaction in data.reactions" :key="reaction.sid">
        <strong>{{ reaction.sid }}</strong> : {{ reaction.equation }}
      </li>
    </ul>

    <form class="model-upload-form">
      <legend>Load Another Model</legend>
      <input ref="upload" type="file" name="file-upload" multiple="" accept="application/JSON" @change="onFileUpload">
    </form>

  </div>
</template>

<script>
import json_data from '../src/assets/test_models/test_data.json'

export default {
  name: 'app',
  data: function() {
    return {
      msg: 'This is a sample SBML Report',
      data: json_data,
    }
  },
  methods: {

    onFileUpload: function(event) {
      let files = event.target.files || event.dataTransfer.files
      if (!files.length) return;
      this.readFile(files[0])
    },

    readFile: function(file) {
      var fileReader = new FileReader();
      fileReader.onload = event => {
        var json_data = JSON.parse(event.target.result)
        this.data = json_data
      };
      fileReader.readAsText(file)
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
