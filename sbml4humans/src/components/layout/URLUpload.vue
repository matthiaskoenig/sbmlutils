<template>
    <div>
        <p>
            Type the URL of an SBML file. Example:
            <code style="font-size: small"
                >https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000001.2?filename=BIOMD0000000001_url.xml</code
            >
        </p>
        <div class="card">
            <div class="p-formgroup-inline">
                <div class="p-field p-col-12">
                    <label for="url" class="p-sr-only">Model URL</label>
                    <InputText
                        ref="url"
                        type="text"
                        class="p-col-12 p-mr-2"
                        :value="modelValue"
                        @input="updateURL"
                        placeholder=""
                    />
                    <Button class="p-mt-2" type="button" @click="submitForm"
                        ><i class="pi pi-upload p-mr-2"></i>Create Report</Button
                    >
                </div>
            </div>
        </div>
        <loading parent="file" />
        <p>
            To embed the report use the
            <code style="font-size: small">{{ frontend_url }}/model_url?url=URL</code>
            endpoint. Example:
            <a :href="example_url">
                <code style="font-size: small">{{ example_url }}</code>
            </a>
        </p>
    </div>
</template>

<script lang="ts">
import store, { VUE_APP_FRONTENDURL } from "@/store/index";
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
        frontend_url(): string {
            return VUE_APP_FRONTENDURL;
        },
        example_url(): string {
            return (
                VUE_APP_FRONTENDURL +
                "/model_url?url=https://raw.githubusercontent.com/matthiaskoenig/sbmlutils/develop/src/sbmlutils/resources/models/glucose/Hepatic_glucose_3.xml"
            );
        },
    },
});
</script>

<style lang="scss" scoped>
p {
    margin: 0;
}
</style>
