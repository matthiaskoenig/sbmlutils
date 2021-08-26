<template>
    <div>
        <FileUpload
            :customUpload="true"
            @uploader="submitForm"
            :multiple="false"
            :showCancelButton="false"
            chooseLabel="Browse"
            uploadLabel="Submit"
            :fileLimit="1"
        >
            <template #empty>
                <p>
                    Drag and drop file to upload. Supported file formats:
                    <code>.xml,.zip,.gz,.bz2</code>
                </p>
            </template>
        </FileUpload>

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

    data(): Record<string, unknown> {
        return {
            file: {
                type: File,
            },
        };
    },

    methods: {
        async submitForm(event): Promise<void> {
            this.file = event.files[0];
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
p {
    margin: 0;
}
</style>
