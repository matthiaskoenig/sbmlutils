<template>
    <div class="container">
        <h1>Upload SBML</h1>
        <form class="needs-validation" @submit.prevent="submitForm">
            <div class="form-row">
                <div class="col-md-12 mb-3">
                    <input
                        type="file"
                        ref="fileField"
                        class="form-control"
                        v-on:change="handleFileUpload()"
                        required
                        title="Click to browse and upload a file from your device"
                    />
                    <div class="invalid-tooltip">
                        Upload a valid SBML file or COMBINE archive containing SBML
                    </div>
                </div>
            </div>
            <button class="btn btn-info w-25" type="submit" style="border-radius: 25px">
                Submit
            </button>
        </form>
        <div class="loader" v-if="loading">
            <span class="loading"><a-spin size="large" /></span>&nbsp;&nbsp;Generating report
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

/**
 * Component to upload an SBML file to generate report.
 */
export default defineComponent({
    data(): Record<string, unknown> {
        return {
            file: {
                type: File,
            },
        };
    },

    methods: {
        /**
         * Sets the currently selected file to the latest uploaded file in the form.
         */
        handleFileUpload(): void {
            const fileField = this.$refs.fileField as HTMLInputElement;
            if (fileField.files != null) {
                this.file = fileField.files[0];
            }
        },

        async submitForm(): Promise<void> {
            let formData = new FormData();
            formData.append("source", this.file as File);

            const headers = {
                "Content-Type": "multipart/form-data",
            };

            const payload = {
                formData: formData,
                headers: headers,
            };

            store.dispatch("fetchReport", payload);
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
@import "@/assets/styles/scss/components/layout/FileUpload.scss";
</style>
