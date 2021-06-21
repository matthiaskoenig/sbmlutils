<template>
    <div class="container">
        <h1>About</h1>
        <div class="section">
            <div class="content">
                <p>
                    The Systems Biology Markup Language (<a href="http://sbml.org"
                                                            target="_blank">SBML</a>) is
                    a standard format for the representation and exchange of biological
                    models. The information in an SBML model file is organized as a list
                    of components encapsulated within the model (e.g. compartments,
                    species, parameters, reactions).
                </p>
                <p>
                    The objective of the project <a
                    href="https://sbml4humans-gsoc-2021.blogspot.com/" target="_blank">SBML4Humans</a>
                    is to provide an interactive and reactive report for SBML models
                    which will allow humans (experts as well as beginners) to easily
                    comprehend the content of a model.
                </p>
            </div>
        </div>

        <!-- Development Team -->
        <div class="section ml-4 mt-3">
            <strong>Development Team</strong>
            <div class="content">
                <ul title="Developers">
                    <li>
                        <a href="https://livermetabolism.com" target="_blank">Dr.
                            Matthias König</a
                        >, Humboldt University, Berlin
                    </li>
                    <li>
                        Dr. Ralf Steuer,
                        Humboldt University, Berlin
                    </li>
                    <li>
                        <a href="https://sankha555.github.io/index" target="_blank"
                        >Sankha Das</a>, BITS Pilani, Rajasthan, India
                    </li>
                </ul>
            </div>
        </div>

        <!-- Funding -->
        <div class="section ml-4 mt-3">
            <strong>Funding</strong>
            <div class="content">
                <ul>
                    <li>
                        <a href="https://summerofcode.withgoogle.com/"
                        >Google Summer of Code 2021</a
                        >
                    </li>
                    <li>Matthias König supported by the Federal Ministry of Education and Research (BMBF, Germany) within the research network Systems Medicine of the Liver (<a href="https://lisym.org/" target="_blank">LiSyM</a>, grant number 031L0054) and by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 "<a href="https://qualiperf.de">QuaLiPerF</a> (Quantifying Liver Perfusion-Function Relationship in Complex Resection - A Systems Medicine Approach)" by grant number 436883643.</li>
                </ul>
            </div>
        </div>

        <!-- Citation -->
        <div class="section ml-4 mt-3">
            <strong>Citation</strong>
            <div class="content">
                <ul>
                    <li><a href="https://zenodo.org/badge/latestdoi/55952847" target="_blank" rel="nofollow"><img alt="Zenodo DOI" src="https://camo.githubusercontent.com/332b1f7dd91e445f074084a39ed733363fa353b257d9e526d489c88dab025172/68747470733a2f2f7a656e6f646f2e6f72672f62616467652f35353935323834372e737667" data-canonical-src="https://zenodo.org/badge/55952847.svg" style="max-width:100%;"></a></li>
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
</template>

<script lang="ts">
import {defineComponent} from "vue";

/**
 * Container to show About info about the project
 *      - team
 *      - licensing
 *      - funding
 *      - citation
 */
export default defineComponent({
    name: "About",
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/About.scss";
</style>