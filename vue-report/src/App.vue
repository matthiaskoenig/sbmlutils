<template>
  <div id="app">
    <page-header></page-header>
    <app-report ref="report"></app-report>
    {{ initial_json }}
  </div>
</template>

<script>
import Header from './components/Header.vue'
import Report from './components/Report.vue'

export default {
  name: 'app',
  components: {
    'page-header': Header,
    'app-report': Report
  },
  data () {
    return {
      msg: 'SBML Report Rendering Prototype',
      initial_json: {}
    }
  },
  created() {
    let json = JSON.parse(document.getElementById("data").textContent)
    this.initial_json = json
  },
  mounted: function(){
    this.$refs.report.updateJSON(this.initial_json)
  },
  methods: {

  },
}
</script>

<style lang="scss">
@import './assets/styles/scss/app.scss';
</style>
