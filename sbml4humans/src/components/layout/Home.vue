<template>
    <div class="container-fluid px-10">
        <div class="row px-5">
            <div class="col-md-6 d-flex flex-column" style="height: 110vh">
                <file-upload-form class="pb-3" />
                <examples-list />
            </div>
            <div class="col-md-6">
                <div class="row">
                    <about class="pb-4" />
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

/* Components */
import ExamplesList from "@/components/layout/ExamplesList.vue";
import FileUploadForm from "@/components/layout/FileUploadForm.vue";
import About from "@/components/layout/About.vue";

/**
 * Component to display the components to appear on the landing page.
 *      - SBML File upload
 *      - List of Examples
 *      - About Info
 */
export default defineComponent({
    components: {
        ExamplesList: ExamplesList,
        FileUploadForm: FileUploadForm,
        About: About,
    },
});
</script>

<style scoped lang="scss"></style>
