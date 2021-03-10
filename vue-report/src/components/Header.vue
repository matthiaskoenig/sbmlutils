<template>
  <header class="header-elem">
    <h3>{{ title }}</h3>
  </header>
</template>

<script>
export default {
  data() {
    return {

    }
  },
  props: {
    title: {
      type: String,
      default: 'SBML Report',
    }
  }
}
</script>

<style lang="scss" scoped>
@import '../assets/styles/scss/header.scss';
@import'~bootstrap/dist/css/bootstrap.css';
</style>
