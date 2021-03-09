<template>
  <div id="app">
    <h1>{{ msg }}</h1>
    <u>
      <h2>Sample SBML Rendering </h2>
    </u>

    <ul>
      <li  id="sample-list" v-for="reaction in reactions" :key="reaction.sid">
        <strong>{{ reaction.sid }}</strong> : {{ reaction.equation }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'app',
  data () {
    return {
      msg: 'This is a sample SBML Report',
      reactions: [
        {
          "sid": "R1",
          "equation" : "Reactant 1 + Reactant 2 ==> Product",
        },
        {
          "sid": "R2",
          "equation" : "Reactant 3 + Reactant 4 ==> Product",
        },
        {
          "sid": "R3",
          "equation" : "Reactant 5 + Reactant 6 ==> Product",
        }
      ]
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
</style>
