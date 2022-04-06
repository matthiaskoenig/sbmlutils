<template>
    <div>
        <p class="p-pb-3">
            Select an SBML file located on your computer. The file can be uncompressed,
            or compressed using zip, gzip or bzip2.
        </p>
        <FileUpload
            :customUpload="true"
            @uploader="submitForm"
            :multiple="false"
            :showCancelButton="false"
            chooseLabel="Browse"
            uploadLabel="Create Report"
            :fileLimit="1"
            :auto="true"
        >
            <template #empty>
                <p>Drag and drop file.</p>
            </template>
        </FileUpload>
        <p class="p-pt-3" style="font-size: smaller">
            By using any part of this service, you agree to the terms of the
            <a
                href="https://github.com/matthiaskoenig/sbmlutils/blob/develop/sbml4humans/privacy_notice.md"
                target="_blank"
                >privacy notice</a
            >.
        </p>
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
