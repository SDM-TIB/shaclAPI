git stash;
git fetch travshacl master; git subtree pull --prefix Trav-SHACL travshacl master --squash;
git fetch s2spy S2Spy; git subtree pull --prefix s2spy s2spy S2Spy --squash;
git stash pop;