<template>
    <div class="home">
        <img alt="Vue logo" src="../assets/images/logo.png" />
        <HelloWorld msg="Generate SBML Model Reports on the go!" />
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";
import HelloWorld from "@/components/HelloWorld.vue"; // @ is an alias to /src

@Options({
    components: {
        HelloWorld,
    },
})
export default class Home extends Vue {}
</script>
