<template>
  <div id="file-upload">
    <form class="file-form">
      <legend>Upload an SBML Model</legend>
      <div class="form-group">
        <label for="fileField">Model File</label>
        <input type="file" class="form-control" id="fileField" @change="onFileUpload">
      </div>
    </form>
  </div>
</template>

<script>
export default{

  data() {
    return {

    }
  },

  props: {

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
        //this.file_contents = json_data
        //this.file_uploaded = true;
        this.$emit('file-changed', json_data)
      };
      fileReader.readAsText(file)
    }

  },

  emits: [
    'file-changed',
  ]
}
</script>

<style lang="scss" scoped>
@import '../assets/styles/scss/fileUpload.scss';
</style>
