<template>
    <div>
        <div class="card">
            <div class="p-formgroup-inline">
                <div class="p-field p-col-12">
                    <label for="url" class="p-sr-only">Model URL</label>
                    <InputText
                        ref="url"
                        type="text"
                        class="p-col-10 p-mr-2"
                        :value="modelValue"
                        @input="updateURL"
                        placeholder="E.g. https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000001.2?filename=BIOMD0000000001_url.xml"
                    />
                    <Button type="button" @click="submitForm"
                        ><i class="pi pi-upload p-mr-2"></i>Submit</Button
                    >
                </div>
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
        updateURL(event): void {
            this.modelValue = event.target.value;
        },

        async submitForm(): Promise<void> {
            store.dispatch("fetchReportUsingURL", this.modelValue);
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
