import Vue from 'vue'
import App from './App.vue'

new Vue({
  el: '#app',
  render: h => h(App),
  methods: {

    onFileChange(event) {
      let files = event.target.files || event.dataTransfer.files
      if (!files.length) return
      this.readFile(files[0])
    },

    readFile(file) {
      var fileReader = new FileReader()
      fileReader.onload = event => {
        var json_data = JSON.parse(e.target.result)
        App.data().data = json_data
      }
      fileReader.readAsText(file)
    }
  }
})
