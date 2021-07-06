<template>
    <div class="container">
        <div class="row">
            <div class="col-md-6">
                <upload-sbml></upload-sbml>
                <examples-list></examples-list>
            </div>
            <div class="col-md-6">
                <about></about>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

/* Components */
import ExamplesListContainer from "@/components/layout/ExamplesListContainer.vue";
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
        "examples-list": ExamplesListContainer,
        "upload-sbml": FileUploadForm,
        about: About,
    },
});
</script>

<style scoped lang="scss">

</style>
