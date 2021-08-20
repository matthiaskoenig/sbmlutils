<template>
    <navbar />
    <div class="p-px-5">

        <div class="p-grid">
            <div class="p-col-12 p-lg-6">
                <file-upload-form/>
                <examples/>
            </div>
            <div class="p-col-12 p-lg-6">
                <about/>
            </div>
        </div>

    </div>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";

/* Components */
import Examples from "@/components/layout/Examples.vue";
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
        Examples,
        FileUploadForm,
        About,
        Navbar,
    },
});
</script>

<style scoped lang="scss"></style>
