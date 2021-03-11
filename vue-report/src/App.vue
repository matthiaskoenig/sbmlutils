<template>
  <div id="app">
    <Header />
    <Report />
  </div>
</template>

<script>
import Header from './components/Header.vue'
import FileUpload from './components/FileUpload.vue'
import Report from './components/Report.vue'

export default {
  name: 'app',
  components: {
    Header,
    FileUpload,
    Report
  },
  data () {
    return {
      msg: 'SBML Report Rendering Prototype'
    }
  },
  methods: {

  }
}
</script>

<style lang="scss">
@import './assets/styles/scss/app.scss';
</style>
