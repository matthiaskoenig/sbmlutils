<template>
    <div class="about-container">
        <h5>About the Project</h5>
        <div class="section">
            <div class="content">
                Systems Biology Markup Language (SBML) is a standard format for the
                representation and exchange of biological models between computers. The
                information in an SBML model file is organized as a list of components
                encapsulated within the model (e.g. compartments, species, parameters,
                reactions, etc.). The objective of the project SBML4Humans is to provide
                an interactive and reactive report for SBML models which will allow
                humans (experts as well as beginners) to easily comprehend the content
                of a model.
            </div>
        </div>

        <!-- Development Team -->
        <div class="section ml-4 mt-3">
            <h6>Development Team</h6>
            <div class="content">
                <ul title="Developers">
                    <li>
                        <a href="mailto:konigmatt@googlemail.com">Dr. Matthias König</a
                        >, Humboldt University, Berlin
                    </li>
                    <li>
                        <a href="mailto:steuer.ralf@googlemail.com">Dr. Ralf Steuer</a>,
                        Humboldt University, Berlin
                    </li>
                    <li>
                        <a href="mailto:f20190029@pilani.bits-pilani.ac.in"
                            >Sankha Das</a
                        >, BITS Pilani, Rajasthan, India
                    </li>
                </ul>
            </div>
        </div>

        <!-- Funding -->
        <div class="section ml-4 d-flex justify-content">
            <div class="mr-auto">
                <h6>Funding</h6>
                <div class="content">
                    <ul title="Funding">
                        <li>
                            <a href="https://summerofcode.withgoogle.com/"
                                >Google Summer of Code 2021</a
                            >
                        </li>
                    </ul>
                </div>
            </div>
            <div class="ml-auto">
                <div class="content">
                    <h6 style="display: inline">Citation</h6>
                    <ul title="Citations">
                        <li>
                            Project Repository:
                            <a href="https://github.com/matthiaskoenig/sbmlutils"
                                >sbmlutils</a
                            >
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
/**
 * Container to show About info about the project
 *      - team
 *      - licensing
 *      - funding
 *      - citation
 */
import { defineComponent } from "vue";

export default defineComponent({
    name: "About",
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/About.scss";
</style>
