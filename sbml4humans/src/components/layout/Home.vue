<template>
    <div class="container">
        <div class="row">
            <file-upload-form class="pb-4"/>
        </div>
        <div class="row">
            <div class="col-md-6">
                <examples-list  class="pb-4"/>
            </div>
            <div class="col-md-6">
                <about  class="pb-4"/>
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

<style scoped lang="scss">

</style>
