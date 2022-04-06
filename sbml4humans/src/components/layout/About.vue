<template>
    <div class="p-px-2">
        <ScrollPanel style="width: 100%">
            <h1>About</h1>
            <Panel header="SBML4Humans">
                <div class="p-d-flex content">
                    <a href="http://sbml.org" class="image">
                        <img src="@/assets/images/sbml-logo.png" height="50" />
                    </a>
                    <p>
                        The Systems Biology Markup Language (<a
                            href="http://sbml.org"
                            target="_blank"
                            >SBML</a
                        >) is a standard format for the representation and exchange of
                        models.
                    </p>
                </div>
                <div class="p-d-flex content">
                    <a href="https://sbml4humans.de" class="image">
                        <img
                            src="@/assets/images/sbml4humans-192x192.png"
                            height="50"
                        />
                    </a>
                    <p>
                        The objective of
                        <a
                            href="https://sbml4humans-gsoc-2021.blogspot.com/"
                            target="_blank"
                        >
                            SBML4Humans
                        </a>
                        is to provide an interactive and reactive report for SBML models
                        which allows humans (experts as well as beginners) to easily
                        comprehend the content of a model. SBML4Humans is part of the
                        <a
                            target="_blank"
                            href="https://github.com/matthiaskoenig/sbmlutils"
                        >
                            sbmlutils
                        </a>
                        project.<br />
                        If you use SBML4Humans in your work cite<br />
                        <a
                            href="https://zenodo.org/badge/latestdoi/55952847"
                            target="_blank"
                            rel="nofollow"
                            ><img
                                class="p-pt-1"
                                alt="Zenodo DOI"
                                src="https://camo.githubusercontent.com/332b1f7dd91e445f074084a39ed733363fa353b257d9e526d489c88dab025172/68747470733a2f2f7a656e6f646f2e6f72672f62616467652f35353935323834372e737667"
                                data-canonical-src="https://zenodo.org/badge/55952847.svg"
                                style="max-width: 100%"
                        /></a>
                    </p>
                </div>
            </Panel>
            <!-- Team -->
            <Panel header="Team">
                <div class="p-d-flex content">
                    <a href="https://livermetabolism.com" class="image">
                        <img src="@/assets/images/people/koenig.png" height="50" />
                    </a>
                    <p>
                        <a href="https://livermetabolism.com" target="_blank"
                            >Dr. Matthias König</a
                        >, Humboldt University, Berlin. Matthias König (PhD. in
                        Biophysics) leads an independent
                        <a href="https://livermetabolism.com" target="_blank"
                            >junior research group</a
                        >
                        for Systems Biology and Systems Medicine of the liver with focus
                        on metabolic research at the Humboldt University Berlin. He has
                        been actively involved in the development of SBML, SED-ML and
                        software supporting these standards.
                    </p>
                </div>
                <div class="p-d-flex content">
                    <a href="https://sankha555.github.io/index" class="image">
                        <img
                            class="img-circle"
                            src="@/assets/images/people/sankha.png"
                            height="50"
                        />
                    </a>
                    <p>
                        <a href="https://sankha555.github.io/index" target="_blank"
                            >Sankha Das</a
                        >, BITS Pilani, Rajasthan, India. Sankha Das (currently pursuing
                        B.E.(Hons.) Computer Science) works as a full-stack web
                        developer in many of his university's student forums and is an
                        active open-source contributor. He is a student member of IEEE,
                        Gujarat section, India and his research interests lie in the
                        fields of cyber security, cryptography and blockchain
                        development.
                    </p>
                </div>
            </Panel>
            <!-- Funding -->
            <Panel header="Funding">
                <div class="p-d-flex content">
                    <a href="https://summerofcode.withgoogle.com/" class="image"
                        ><img src="@/assets/images/gsoc.png" width="50"
                    /></a>
                    <p>
                        SBML4Humans was supported by
                        <a href="https://summerofcode.withgoogle.com/" target="_blank"
                            >Google Summer of Code 2021</a
                        >, a global program focused on bringing more student developers
                        into open source software development. Sankha worked within the
                        open source organization
                        <a href="https://nrnb.org/" target="_blank"
                            >National Resource for Network Biology (NRNB)</a
                        >
                        over 10 weeks on SBML4Humans.
                    </p>
                </div>
                <div class="p-d-flex content">
                    <a href="https://lisym.org/" class="image"
                        ><img src="@/assets/images/lisym.png" width="50"
                    /></a>
                    <p>
                        Matthias König is supported by the Federal Ministry of Education
                        and Research (BMBF, Germany) within the research network Systems
                        Medicine of the Liver (<a
                            href="https://lisym.org/"
                            target="_blank"
                            >LiSyM</a
                        >, grant number 031L0054).
                    </p>
                </div>
                <div class="p-d-flex content">
                    <p>
                        Matthias König is supported by the German Research Foundation
                        (DFG) within the Research Unit Programme FOR 5151 "<a
                            href="https://qualiperf.de"
                            >QuaLiPerF</a
                        >
                        (Quantifying Liver Perfusion-Function Relationship in Complex
                        Resection - A Systems Medicine Approach)" by grant number
                        436883643.
                    </p>
                </div>
            </Panel>
        </ScrollPanel>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

export default defineComponent({
    name: "About",
});
</script>

<style lang="scss" scoped>
.image {
    max-width: 100%;
    height: auto;
    margin: auto 30px;
}

.content {
    text-align: justify;
}

.img-circle {
    border-radius: 50%;
}
</style>
