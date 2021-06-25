<template>
    <div class="home">
        <HomeInfo />
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";
import HomeInfo from "@/components/layout/HomeInfo.vue";

@Options({
    components: {
        HomeInfo,
    },
})
export default class Home extends Vue {}
</script>
