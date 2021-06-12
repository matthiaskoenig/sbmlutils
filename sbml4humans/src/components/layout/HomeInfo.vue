<template>
    <div class="divider">
        <div class="left-container">
            <div class="file-upload">
                <upload-sbml></upload-sbml>
            </div>
            <div class="about">
                <about></about>
            </div>
        </div>
        <div class="right-container">
            <examples-list></examples-list>
        </div>
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";

/* Components */
import ExamplesListContainer from "@/components/layout/ExamplesListContainer.vue";
import FileUploadForm from "@/components/layout/FileUploadForm.vue";
import About from "@/components/layout/About.vue";

@Options({
    components: {
        "examples-list": ExamplesListContainer,
        "upload-sbml": FileUploadForm,
        about: About,
    },

    props: {
        msg: String,
    },
})
export default class HomeInfo extends Vue {
    msg!: string;
}
</script>

<style scoped lang="scss">
@import "@/assets/styles/scss/components/layout/HomeInfo.scss";
</style>
