<template>
    <div>
        <h1>Upload SBML</h1>
        <form class="needs-validation" @submit.prevent="submitForm">
            <div class="mb-3">
                <input
                    type="file"
                    ref="fileField"
                    class="form-control"
                    v-on:change="handleFileUpload()"
                    required
                    title="Click to browse and upload a file from your device"
                />
            </div>
            <button class="btn btn-primary" type="submit">Submit</button>
            <div class="invalid-tooltip">
                Upload a valid SBML file or COMBINE archive containing SBML
            </div>
        </form>
        <loading parent="file"></loading>
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
        loading: Loading,
    },

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

<style lang="scss" scoped></style>
