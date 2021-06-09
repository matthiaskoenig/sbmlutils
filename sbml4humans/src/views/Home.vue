<template>
    <div class="home">
        <HomeInfo msg="Generate SBML Model Reports on the go!" />
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";
import HomeInfo from "@/components/layout/HomeInfo.vue"; // @ is an alias to /src

@Options({
    components: {
        HomeInfo,
    },
})
export default class Home extends Vue {}
</script>
