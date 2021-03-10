<template>
  <div id="report">
    <h2>SBML Model: {{ json_data.model_name }} [{{ json_data.model_sid }}]</h2>
    <br>
    <div class="row">
      <div class="column-left">
        <div class="container">
          <h4 v-if="json_data.msg">{{ json_data.msg }}</h4>
          <br>
          <ul>
            <li  id="sample-list" v-for="reaction in json_data.reactions" :key="reaction.sid">
              <strong>{{ reaction.sid }}</strong> : {{ reaction.equation }}
            </li>
          </ul>
        </div>
      </div>
      <div class="column-right">
        <FileUpload @file-changed="updateJSON" />
      </div>
    </div>
  </div>
</template>

<script>
import FileUpload from './FileUpload'

export default {
  data() {
    return {
      json_data: {
        "model_sid" : this.modelSID,
        "model_name" : this.modelName,
        "msg" : "Upload an SBML Model to render HTML report"
      },
    }
  },

  components: {
    FileUpload,
  },

  props: {
    modelSID: {
      type: String,
      default: "Model-SID"
    },
    modelName: {
      type: String,
      default: "Model-Name"
    },
  },

  methods: {
    updateJSON: function(data) {
      this.json_data = data
    }
  }
}
</script>

<style lang="scss" scoped>
@import '../assets/styles/scss/report.scss';
</style>
