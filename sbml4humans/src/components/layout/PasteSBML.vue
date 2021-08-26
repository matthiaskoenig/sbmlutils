<template>
    <div>
        <div class="p-formgroup-inline">
            <p class="p-ml-2">Paste or type SBML contents below.</p>
            <div class="p-col-12">
                <Textarea
                    type="text"
                    class="p-col-12 p-mr-2"
                    style="resize: none"
                    rows="5"
                    :value="modelValue"
                    @input="updateContent"
                    :autoResize="false"
                />
                <Button class="p-mt-2" type="button" @click="submitForm"
                    ><i class="pi pi-upload p-mr-2"></i>Create Report</Button
                >
            </div>
        </div>
        <loading parent="file" />
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

import Loading from "@/components/layout/Loading.vue";
/**
 * Component to upload an SBML file to generate report.
 */
export default defineComponent({
    components: {
        Loading,
    },

    data() {
        return {
            modelValue: "",
        };
    },

    methods: {
        updateContent(event): void {
            this.modelValue = event.target.value;
        },

        async submitForm(): Promise<void> {
            store.dispatch("fetchReportUsingSBMLContent", this.modelValue);
        },
    },

    computed: {
        loading(): boolean {
            return store.state.fileLoading;
        },
    },
});
</script>

<style lang="scss" scoped>
p {
    margin: 0;
}
</style>
