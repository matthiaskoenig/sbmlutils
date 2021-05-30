<template>
    <div class="home">
        <img alt="SBML logo" src="@/assets/images/logo.png" />
        <HomeInfo msg="Generate SBML Model Reports on the go!" />
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";
import HomeInfo from "@/components/HomeInfo.vue"; // @ is an alias to /src
import createStore from "@/store/index";

@Options({
    components: {
        HomeInfo,
    },
})

export default class Home extends Vue {}
</script>
