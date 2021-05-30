<template>
    <form @submit.prevent="getExample()">
        <button class="btn list-item" type="submit">
            {{ exampleName }}
        </button>
    </form>
</template>

<script>
import axios from "axios";

import BASE_URLS from "@/data/urls";

export default {
    props: {
        exampleName: {
            type: String,
            default: "Model Name",
        },
        exampleId: {
            type: String,
            default: "example-id",
        },
    },

    methods: {
        async getExample() {
            const url = BASE_URLS.API_BASE_URL + "/examples/" + this.exampleId;
            const res = await axios.get(url);

            if (res.status === 200) {
                alert("SUCCESS: " + res.data.debug.json_report_time);
            } else {
                alert("FAILURE");
            }
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/Example.scss";
</style>
