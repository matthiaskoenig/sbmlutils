<template>
    <navbar />
    <div class="p-px-5">
        <div class="p-grid">
            <div class="p-col-6 p-d-flex p-flex-column" style="height: 130vh">
                <file-upload-form class="p-pb-3" />
                <examples-list />
            </div>
            <div class="p-col-6">
                <about class="p-pb-4" />
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
import Navbar from "@/components/layout/Navbar.vue";

/**
 * Component to display the components to appear on the landing page.
 *      - SBML File upload
 *      - List of Examples
 *      - About Info
 */
export default defineComponent({
    components: {
        ExamplesList,
        FileUploadForm,
        About,
        Navbar,
    },
});
</script>

<style scoped lang="scss"></style>
