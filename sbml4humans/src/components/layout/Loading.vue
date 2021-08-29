<template>
    <Dialog
        :header="message"
        footer="&nbsp;"
        v-model:visible="loading"
        :style="{ width: '40vw' }"
        :breakpoints="{ '960px': '75vw', '640px': '100vw' }"
        :modal="true"
        :closable="false"
    >
        <ProgressBar class="p-my-5" mode="indeterminate" style="height: 0.5em" />
        This may take a few seconds. Please be patient.
    </Dialog>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
    props: {
        parent: {
            type: String,
            required: true,
        },
        message: {
            type: String,
            required: false,
            default: "Creating SBML report",
        },
    },
    computed: {
        loading(): boolean {
            let key: string = this.parent + "Loading";
            return store.state[key];
        },
    },
});
</script>

<style lang="scss" scoped></style>
